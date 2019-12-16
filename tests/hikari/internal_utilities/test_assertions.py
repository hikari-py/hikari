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
import pytest

from hikari.internal_utilities import assertions
from tests.hikari import _helpers


@_helpers.assert_does_not_raise(type_=ValueError)
def test_assert_that_when_True():
    assertions.assert_that(True)


@_helpers.assert_raises(type_=ValueError)
def test_assert_that_when_False():
    assertions.assert_that(False, "bang")


@_helpers.assert_raises(type_=ValueError)
def test_assert_not_none_when_none():
    assertions.assert_not_none(None)


@pytest.mark.parametrize("arg", [9, "foo", False, 0, 0.0, "", [], {}, set(), ..., NotImplemented])
@_helpers.assert_does_not_raise(type_=ValueError)
def test_assert_not_none_when_not_none(arg):
    assertions.assert_not_none(arg)


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_mixin_applied_to_something_that_is_not_a_class():
    @assertions.assert_is_mixin
    def foo():
        pass


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_object_or_mixin():
    class Bar:
        pass

    @assertions.assert_is_mixin
    class FooMixin(Bar):
        pass


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_mixin_applied_to_something_that_is_not_slotted():
    @assertions.assert_is_mixin
    class FooMixin:
        pass


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_mixin_applied_to_something_that_is_slotted_but_not_multiple_inheritance_compatible():
    @assertions.assert_is_mixin
    class FooMixin:
        __slots__ = ("nine", "eighteen", "twentyseven")


@_helpers.assert_does_not_raise(type_=TypeError)
def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_mixins_and_directly_from_object():
    @assertions.assert_is_mixin
    class BarMixin:
        __slots__ = ()

    @assertions.assert_is_mixin
    class FooMixin(BarMixin):
        __slots__ = ()


@_helpers.assert_does_not_raise(type_=TypeError)
def test_assert_subclasses_happy_path():
    class A:
        pass

    class B(A):
        pass

    assertions.assert_subclasses(B, A)


@_helpers.assert_raises(type_=TypeError)
def test_assert_subclasses_sad_path():
    class A:
        pass

    class B:
        pass

    assertions.assert_subclasses(B, A)


@_helpers.assert_does_not_raise(type_=TypeError)
def test_assert_is_instance_happy_path():
    class A:
        pass

    class B(A):
        pass

    assertions.assert_is_instance(B(), B)
    assertions.assert_is_instance(B(), A)


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_instance_sad_path():
    class A:
        pass

    class B:
        pass

    assertions.assert_is_instance(B(), A)


@_helpers.assert_does_not_raise(type_=ValueError)
def test_assert_is_natural_happy_path():
    assertions.assert_is_natural(0)
    assertions.assert_is_natural(1)
    assertions.assert_is_natural(
        99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999
    )


@_helpers.assert_raises(type_=ValueError)
def test_assert_is_natural_wrong_type():
    assertions.assert_is_natural(1.0)


@_helpers.assert_raises(type_=ValueError)
def test_assert_is_natural_wrong_value():
    assertions.assert_is_natural(-1)


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_slotted_on_non_slotted_case():
    @assertions.assert_is_slotted
    class NotSlotted:
        pass


@_helpers.assert_raises(type_=TypeError)
def test_assert_is_slotted_on_non_slotted_case():
    @assertions.assert_is_slotted
    class NotSlotted:
        pass


@_helpers.assert_does_not_raise(type_=TypeError)
def test_assert_is_slotted_on_slotted_case():
    @assertions.assert_is_slotted
    class Slotted:
        __slots__ = ("foo", "bar", "baz")


@_helpers.assert_does_not_raise(type_=TypeError)
def test_assert_not_slotted_on_non_slotted_case():
    @assertions.assert_not_slotted
    class NotSlotted:
        pass


@_helpers.assert_raises(type_=TypeError)
def test_assert_not_slotted_on_slotted_case():
    @assertions.assert_not_slotted
    class Slotted:
        __slots__ = ("foo", "bar", "baz")
