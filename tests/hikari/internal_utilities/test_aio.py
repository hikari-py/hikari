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
import asyncio

import asyncmock as mock
import pytest

from hikari.internal_utilities.aio import optional_await


class CoroutineStub:
    def __init__(self, *args, **kwargs):
        self.awaited = False
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        return isinstance(other, CoroutineStub) and self.args == other.args and self.kwargs == other.kwargs

    def __await__(self):
        self.awaited = True
        yield from asyncio.sleep(0.01).__await__()

    def __repr__(self):
        args = ", ".join(map(repr, self.args))
        kwargs = ", ".join(map(lambda k, v: f"{k!s}={v!r}", self.kwargs.items()))
        return f"({args}, {kwargs})"


class CoroutineFunctionStub:
    def __call__(self, *args, **kwargs):
        return CoroutineStub(*args, **kwargs)


def test_coro_stub_eq():
    assert CoroutineStub(9, 18, x=27) == CoroutineStub(9, 18, x=27)


def test_coro_stub_neq():
    assert CoroutineStub(9, 18, x=27) != CoroutineStub(9, 18, x=36)


@pytest.mark.asyncio
async def test_optional_await_gets_run_with_await():
    coro_fn = CoroutineFunctionStub()

    wrapped_coro_fn = optional_await()(coro_fn)

    with mock.patch("hikari.internal_utilities.compat.asyncio.create_task", new=mock.AsyncMock()) as create_task:
        await wrapped_coro_fn(9, 18, 27)
        create_task.assert_called_with(coro_fn(9, 18, 27), name=None)


@pytest.mark.asyncio
async def test_optional_await_gets_run_without_await():
    coro_fn = CoroutineFunctionStub()

    wrapped_coro_fn = optional_await()(coro_fn)

    with mock.patch("hikari.internal_utilities.compat.asyncio.create_task") as create_task:
        wrapped_coro_fn(9, 18, 27)
        create_task.assert_called_with(coro_fn(9, 18, 27), name=None)


@pytest.mark.asyncio
async def test_optional_await_with_description():
    coro_fn = CoroutineFunctionStub()

    wrapped_coro_fn = optional_await("foo")(coro_fn)

    with mock.patch("hikari.internal_utilities.compat.asyncio.create_task", new=mock.AsyncMock()) as create_task:
        await wrapped_coro_fn(9, 18, 27)
        create_task.assert_called_with(coro_fn(9, 18, 27), name="foo")


@pytest.mark.asyncio
async def test_optional_await_shielded():
    coro_fn = CoroutineFunctionStub()
    wrapped_coro_fn = optional_await(shield=True)(coro_fn)

    shielded_coro = CoroutineStub()

    with mock.patch("asyncio.shield", new=mock.MagicMock(return_value=shielded_coro)) as shield:
        with mock.patch("hikari.internal_utilities.compat.asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await wrapped_coro_fn(9, 18, 27)
            shield.assert_called_with(coro_fn(9, 18, 27))
            create_task.assert_called_with(shielded_coro, name=None)
