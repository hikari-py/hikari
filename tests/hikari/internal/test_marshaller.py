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
import attr
import mock
import pytest

from hikari.internal import marshaller, codes
from tests.hikari import _helpers


class TestDereferenceHandle:
    def test_dereference_handle_module_only(self):
        from concurrent import futures

        assert marshaller.dereference_handle("concurrent.futures") is futures

    def test_dereference_handle_module_and_attribute(self):
        assert (
            marshaller.dereference_handle("hikari.internal.codes#_GatewayCloseCode.AUTHENTICATION_FAILED")
            is codes.GatewayCloseCode.AUTHENTICATION_FAILED
        )


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
                inherit_kwargs=True,
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
                    marshaller._INHERIT_KWARGS: True,
                    marshaller._IF_UNDEFINED: mock_default_factory_2,
                    marshaller._IF_NONE: mock_default_factory_1,
                    marshaller._MARSHALLER_ATTRIB: True,
                },
                repr=False,
            )


@pytest.mark.parametrize("data", [2, "d", bytes("ok", "utf-8"), [], {}, set()])
@_helpers.assert_raises(type_=RuntimeError)
def test_default_validator_raises_runtime_error(data):
    marshaller._default_validator(data)


def method_stub(value):
    ...


@pytest.mark.parametrize(
    "data", [lambda x: "ok", *marshaller._PASSED_THROUGH_SINGLETONS, marshaller.RAISE, dict, method_stub]
)
def test_default_validator(data):
    marshaller._default_validator(data)


class TestAttrs:
    def test_invokes_attrs(self):
        marshaller_mock = mock.MagicMock(marshaller.HikariEntityMarshaller)

        kwargs = {"marshaller": marshaller_mock}

        marshaller_mock.register = mock.MagicMock(wraps=lambda c: c)

        @marshaller.marshallable(**kwargs)
        @attr.s()
        class Foo:
            bar = 69

        assert Foo is not None
        assert Foo.bar == 69

        marshaller_mock.register.assert_called_once_with(Foo)


class TestMarshaller:
    @pytest.fixture()
    def marshaller_impl(self):
        return marshaller.HikariEntityMarshaller()

    @_helpers.assert_raises(type_=TypeError)
    def test_register_raises_type_error_on_none_attr_class(self, marshaller_impl):
        defaulted_foo = mock.MagicMock()

        @marshaller.marshallable(marshaller=marshaller_impl)
        class User:
            id: int = marshaller.attrib(deserializer=int)
            foo: list = attr.attrib(default=defaulted_foo)

    def test_register_ignores_none_marshaller_attrs(self, marshaller_impl):
        defaulted_foo = mock.MagicMock()

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=int)
            foo: list = attr.attrib(default=defaulted_foo)

        result = marshaller_impl.deserialize({"id": "123", "foo": "blah"}, User)
        assert result.id == 123
        assert result.foo is defaulted_foo

    def test_deserialize(self, marshaller_impl):
        deserialized_id = mock.MagicMock()
        id_deserializer = mock.MagicMock(return_value=deserialized_id)

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=id_deserializer)
            some_list: list = marshaller.attrib(deserializer=lambda items: [str(i) for i in items])

        result = marshaller_impl.deserialize({"id": "12345", "some_list": [True, False, "foo", 12, 3.4]}, User)

        assert isinstance(result, User)
        assert result.id == deserialized_id
        assert result.some_list == ["True", "False", "foo", "12", "3.4"]

    def test_deserialize_not_required_success_if_specified(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_undefined=None, deserializer=str)

        result = marshaller_impl.deserialize({"id": 12345}, User)

        assert isinstance(result, User)
        assert result.id == "12345"

    @pytest.mark.parametrize("singleton", marshaller._PASSED_THROUGH_SINGLETONS)
    def test_deserialize_not_required_success_if_not_specified(self, marshaller_impl, singleton):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_undefined=singleton, deserializer=str)

        result = marshaller_impl.deserialize({}, User)

        assert isinstance(result, User)
        assert result.id is singleton

    def test_deserialize_calls_if_undefined_if_not_none_and_field_not_present(self, marshaller_impl):
        mock_result = mock.MagicMock()
        mock_callable = mock.MagicMock(return_value=mock_result)

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_undefined=mock_callable, deserializer=str)

        result = marshaller_impl.deserialize({}, User)

        assert isinstance(result, User)
        assert result.id is mock_result
        mock_callable.assert_called_once()

    @_helpers.assert_raises(type_=AttributeError)
    def test_deserialize_fail_on_unspecified_if_required(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=str)

        marshaller_impl.deserialize({}, User)

    def test_deserialize_nullable_success_if_not_null(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_none=None, deserializer=str)

        result = marshaller_impl.deserialize({"id": 12345}, User)

        assert isinstance(result, User)
        assert result.id == "12345"

    @pytest.mark.parametrize("singleton", marshaller._PASSED_THROUGH_SINGLETONS)
    def test_deserialize_nullable_success_if_null(self, marshaller_impl, singleton):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_none=singleton, deserializer=str)

        result = marshaller_impl.deserialize({"id": None}, User)

        assert isinstance(result, User)
        assert result.id is singleton

    def test_deserialize_calls_if_none_if_not_none_and_data_is_none(self, marshaller_impl):
        mock_result = mock.MagicMock()
        mock_callable = mock.MagicMock(return_value=mock_result)

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(if_none=mock_callable, deserializer=str)

        result = marshaller_impl.deserialize({"id": None}, User)

        assert isinstance(result, User)
        assert result.id is mock_result
        mock_callable.assert_called_once()

    @_helpers.assert_raises(type_=AttributeError)
    def test_deserialize_fail_on_None_if_not_nullable(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=str)

        marshaller_impl.deserialize({"id": None}, User)

    @_helpers.assert_raises(type_=TypeError)
    def test_deserialize_fail_on_Error(self, marshaller_impl):
        die = mock.MagicMock(side_effect=RuntimeError)

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=die)

        marshaller_impl.deserialize({"id": 123,}, User)

    def test_serialize(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=..., serializer=str)
            some_list: list = marshaller.attrib(deserializer=..., serializer=lambda i: list(map(int, i)))

        u = User(12, ["9", "18", "27", "36"])

        assert marshaller_impl.serialize(u) == {"id": "12", "some_list": [9, 18, 27, 36]}

    def test_serialize_skips_fields_with_null_serializer(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User:
            id: int = marshaller.attrib(deserializer=..., serializer=str)
            some_list: list = marshaller.attrib(
                deserializer=..., serializer=None,
            )

        u = User(12, ["9", "18", "27", "36"])

        assert marshaller_impl.serialize(u) == {
            "id": "12",
        }

    def test_deserialize_skips_fields_with_null_deserializer(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s
        class User:
            username: str = marshaller.attrib(deserializer=str)
            _component: object = marshaller.attrib(deserializer=None, default=None)

        u = marshaller_impl.deserialize({"_component": "OK", "component": "Nay", "username": "Nay"}, User)
        assert u._component is None
        assert u.username == "Nay"

    def test_deserialize_kwarg_gets_set_for_skip_unmarshalling_attr(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s
        class User:
            _component: object = marshaller.attrib(deserializer=None, default=None)

        mock_component = mock.MagicMock()
        u = marshaller_impl.deserialize({"_component": "OK", "component": "Nay"}, User, component=mock_component)
        assert u._component is mock_component

    def test_deserialize_injects_kwargs_to_inheriting_child_entity(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class Child:
            _components: object = marshaller.attrib(deserializer=None, serializer=None)

        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class User(Child):
            child: Child = marshaller.attrib(
                deserializer=lambda *args, **kwargs: marshaller_impl.deserialize(*args, Child, **kwargs),
                inherit_kwargs=True,
            )

        components = mock.MagicMock()

        user = marshaller_impl.deserialize({"child": {}}, User, components=components)
        assert user._components is components
        assert user.child._components is components

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
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class ClassWithUnderscores:
            _foo = marshaller.attrib(deserializer=str)

        impl = marshaller_impl.deserialize({"_foo": 1234}, ClassWithUnderscores)

        assert impl._foo == "1234"

    def test_handling_underscores_correctly_during_serialization(self, marshaller_impl):
        @marshaller.marshallable(marshaller=marshaller_impl)
        @attr.s()
        class ClassWithUnderscores:
            _foo = marshaller.attrib(serializer=int)

        impl = ClassWithUnderscores(foo="1234")

        assert marshaller_impl.serialize(impl) == {"_foo": 1234}
