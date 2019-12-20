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

from hikari.internal_utilities import meta
from tests.hikari import _helpers


class TestDeprecation:
    def test_deprecated_function_no_alts(self):
        @meta.deprecated()
        def deprecated_func(a, b, c):
            return a + b * c

        with _helpers.AssertWarns(
            pattern=r".*\.deprecated_func\(a, b, c\)` is deprecated", category=DeprecationWarning
        ):
            assert deprecated_func(9, 18, 27) == 495

    def test_deprecated_function_alts(self):
        async def foobar(foo, bar):
            pass

        @property
        def bazbork():
            pass

        @meta.deprecated(foobar, bazbork, "i like shorts they are comfy and easy to wear")
        def deprecated_func(a, b, c):
            return a + b * c

        with _helpers.AssertWarns(
            pattern=r"function .*\.deprecated_func\(a, b, c\)` is deprecated", category=DeprecationWarning
        ) as ctx:
            assert deprecated_func(9, 18, 27) == 495
        ctx.matched_message_contains(r"`coroutine function .*foobar\(foo, bar\)`")
        ctx.matched_message_contains(r"property")
        ctx.matched_message_contains(r"`i like shorts they are comfy and easy to wear`")

    @pytest.mark.asyncio
    async def test_deprecated_class(self):
        async def foobar(foo, bar):
            pass

        @property
        def bazbork():
            pass

        @meta.deprecated()
        class DeprecatedKlazz:
            @staticmethod
            def __new__(cls):
                # Force this signature to not take args or kwargs, i don't trust that cls got passed correctly
                # without trying this
                return super().__new__(cls)

        with _helpers.AssertWarns(
            pattern=r"class .*\.DeprecatedKlazz` is deprecated", category=DeprecationWarning
        ) as ctx:
            assert isinstance(DeprecatedKlazz(), DeprecatedKlazz)

    def test_deprecated_metaclass(self):
        async def foobar(foo, bar):
            pass

        @property
        def bazbork():
            pass

        @meta.deprecated()
        class DeprecatedMetaKlazz(type):
            @staticmethod
            def __new__(mcs, name, bases, namespace):
                return super().__new__(mcs, name, bases, namespace)

        with _helpers.AssertWarns(
            pattern=r"metaclass .*\.DeprecatedMetaKlazz` is deprecated", category=DeprecationWarning
        ) as ctx:

            class DeprecatedKlazz(metaclass=DeprecatedMetaKlazz):
                pass

            assert isinstance(DeprecatedKlazz, DeprecatedMetaKlazz)
