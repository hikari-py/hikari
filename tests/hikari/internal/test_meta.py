#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
from hikari.internal import meta


def test_SingletonMeta():
    class StubSingleton(metaclass=meta.SingletonMeta):
        pass

    assert StubSingleton() is StubSingleton()


class TestUniqueFunctionMeta:
    def test_raises_type_error_on_duplicated_methods(self):
        class StubMixin1(metaclass=meta.UniqueFunctionMeta):
            def foo(self):
                ...

            def bar(cls):
                ...

        class StubMixin2(metaclass=meta.UniqueFunctionMeta):
            def foo(cls):
                ...

            def baz(cls):
                ...

        try:

            class Impl(StubMixin1, StubMixin2):
                ...

            assert False, "Should've raised a TypeError on overwritten function."
        except TypeError:
            pass

    def test_passes_when_no_duplication_present(self):
        class StubMixin1(metaclass=meta.UniqueFunctionMeta):
            def foo(self):
                ...

            def bar(cls):
                ...

        class StubMixin2(metaclass=meta.UniqueFunctionMeta):
            def baz(cls):
                ...

        class Impl(StubMixin1, StubMixin2):
            ...

    def test_allows_duplicate_methods_when_inherited_from_same_base_further_up(self):
        class StubMixin0(metaclass=meta.UniqueFunctionMeta):
            def nyaa(self):
                ...

        class StubMixin1(StubMixin0):
            ...

        class StubMixin2(StubMixin0):
            ...

        class Impl(StubMixin1, StubMixin2):
            ...
