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
import sys
import typing

import asyncmock
import pytest

from hikari.internal_utilities import compat


def if_version(expr):
    def decorator(test):
        if eval("__import__('sys').version_info " + expr):
            return test

    return decorator


@if_version("< (3, 8)")
@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["name", None])
async def test_asyncio_create_task_lt_38(name):
    with asyncmock.patch("asyncio.create_task") as create_task:
        coro = asyncmock.MagicMock()
        compat.asyncio.create_task(coro, name=name)
        create_task.assert_called_with(coro)


@if_version(">= (3, 8)")
@pytest.mark.asyncio
@pytest.mark.parametrize("name", ["name", None])
async def test_asyncio_create_task_gte_38(name):
    with asyncmock.patch("asyncio.create_task") as create_task:
        coro = asyncmock.MagicMock()
        compat.asyncio.create_task(coro, name=name)
        create_task.assert_called_with(coro, name=name)


def test_Protocol():
    T = typing.TypeVar("T")

    class Protocol(compat.typing.Protocol[T]):
        def foo(self) -> T:
            ...

    class Impl(Protocol[int]):
        def foo(self):
            return 123

    assert Impl().foo() == 123
