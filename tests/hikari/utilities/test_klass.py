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
import pytest

from hikari.utilities import klass


def test_SingletonMeta():
    class StubSingleton(metaclass=klass.SingletonMeta):
        pass

    assert StubSingleton() is StubSingleton()


def test_Singleton():
    class StubSingleton(klass.Singleton):
        pass

    assert StubSingleton() is StubSingleton()


class Class:
    pass


@pytest.mark.parametrize(
    ["args", "expected_name"],
    [
        ([Class], f"{__name__}.Class"),
        ([Class()], f"{__name__}.Class"),
        ([Class, "Foooo", "bar", "123"], f"{__name__}.Class.Foooo.bar.123"),
        ([Class(), "qux", "QUx", "940"], f"{__name__}.Class.qux.QUx.940"),
    ],
)
def test_get_logger(args, expected_name):
    assert klass.get_logger(*args).name == expected_name
