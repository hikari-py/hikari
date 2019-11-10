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
import pytest

from hikari.internal_utilities import assertions
from tests.hikari import _helpers


def test_assert_that_when_True():
    assertions.assert_that(True)


def test_assert_that_when_False():
    try:
        assertions.assert_that(False, "bang")
    except ValueError as ex:
        assert str(ex) == "bang"


def test_assert_not_none_when_none():
    try:
        assertions.assert_not_none(None)
        assert False, "No error raised"
    except ValueError:
        pass


@pytest.mark.parametrize("arg", [9, "foo", False, 0, 0.0, "", [], {}, set(), ..., NotImplemented])
def test_assert_not_none_when_not_none(arg):
    assertions.assert_not_none(arg)


def test_assert_is_mixin_applied_to_something_that_is_not_a_class():
    try:

        @assertions.assert_is_mixin
        def foo():
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_object_or_mixin():
    try:

        class Bar:
            pass

        @assertions.assert_is_mixin
        class FooMixin(Bar):
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_not_slotted():
    try:

        @assertions.assert_is_mixin
        class FooMixin:
            pass

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_slotted_but_not_multiple_inheritance_compatible():
    try:

        @assertions.assert_is_mixin
        class FooMixin:
            __slots__ = ("nine", "eighteen", "twentyseven")

        assert False, "No error thrown"
    except TypeError:
        pass


def test_assert_is_mixin_applied_to_something_that_is_directly_derived_from_mixins_and_directly_from_object():
    @assertions.assert_is_mixin
    class BarMixin:
        __slots__ = ()

    @assertions.assert_is_mixin
    class FooMixin(BarMixin):
        __slots__ = ()


def test_assert_subclasses_happy_path():
    class A:
        pass

    class B(A):
        pass

    assertions.assert_subclasses(B, A)


@_helpers.assert_raises(TypeError)
def test_assert_subclasses_sad_path():
    class A:
        pass

    class B:
        pass

    assertions.assert_subclasses(B, A)


def test_assert_is_instance_happy_path():
    class A:
        pass

    class B(A):
        pass

    assertions.assert_is_instance(B(), B)
    assertions.assert_is_instance(B(), A)


@_helpers.assert_raises(TypeError)
def test_assert_is_instance_sad_path():
    class A:
        pass

    class B:
        pass

    assertions.assert_is_instance(B(), A)


def test_assert_is_natural_happy_path():
    assertions.assert_is_natural(0)
    assertions.assert_is_natural(1)
    assertions.assert_is_natural(
        99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999
    )


@_helpers.assert_raises(ValueError)
def test_assert_is_natural_wrong_type():
    assertions.assert_is_natural(1.0)


@_helpers.assert_raises(ValueError)
def test_assert_is_natural_wrong_value():
    assertions.assert_is_natural(-1)
