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
import cymock as mock

import pytest

from hikari.internal_utilities import aio
from tests.hikari import _helpers


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


class TestCoroutineFunctionStubUsedInTests:
    def test_coro_stub_eq(self):
        assert CoroutineStub(9, 18, x=27) == CoroutineStub(9, 18, x=27)

    # POC for the stuff we use in tests
    def test_coro_stub_neq(self):
        assert CoroutineStub(9, 18, x=27) != CoroutineStub(9, 18, x=36)


class TestOptionalAwait:
    @pytest.mark.asyncio
    async def test_optional_await_gets_run_with_await(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await()(coro_fn)

        with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name=None)

    @pytest.mark.asyncio
    async def test_optional_await_gets_run_without_await(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await()(coro_fn)

        with mock.patch("asyncio.create_task") as create_task:
            wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name=None)

    @pytest.mark.asyncio
    async def test_optional_await_with_description(self):
        coro_fn = CoroutineFunctionStub()

        wrapped_coro_fn = aio.optional_await("foo")(coro_fn)

        with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
            await wrapped_coro_fn(9, 18, 27)
            create_task.assert_called_with(coro_fn(9, 18, 27), name="foo")

    @pytest.mark.asyncio
    async def test_optional_await_shielded(self):
        coro_fn = CoroutineFunctionStub()
        wrapped_coro_fn = aio.optional_await(shield=True)(coro_fn)

        shielded_coro = CoroutineStub()

        with mock.patch("asyncio.shield", new=mock.MagicMock(return_value=shielded_coro)) as shield:
            with mock.patch("asyncio.create_task", new=mock.AsyncMock()) as create_task:
                await wrapped_coro_fn(9, 18, 27)
                shield.assert_called_with(coro_fn(9, 18, 27))
                create_task.assert_called_with(shielded_coro, name=None)


class TestEventDelegate:
    @pytest.fixture
    def mux_map(self):
        return aio.EventDelegate()

    # noinspection PyTypeChecker
    @_helpers.assert_raises(type_=TypeError)
    def test_add_not_coroutine_function(self, mux_map):
        mux_map.add("foo", lambda: None)

    def test_add_coroutine_function_when_no_others_with_name(self, mux_map):
        async def coro_fn():
            pass

        mux_map.add("foo", coro_fn)
        assert coro_fn in mux_map._muxes["foo"]

    def test_add_coroutine_function_when_list_exists(self, mux_map):
        async def coro_fn1():
            pass

        async def coro_fn2():
            pass

        mux_map.add("foo", coro_fn1)
        mux_map.add("foo", coro_fn2)
        assert coro_fn1 in mux_map._muxes["foo"]
        assert coro_fn2 in mux_map._muxes["foo"]

    def test_remove_non_existing_mux_list(self, mux_map):
        async def remove_this():
            pass

        # should not raise
        mux_map.remove("foo", remove_this)

    def test_remove_non_existing_mux(self, mux_map):
        mux_map._muxes["foo"] = []

        async def remove_this():
            pass

        # should not raise
        mux_map.remove("foo", remove_this)

    def test_remove_when_list_left_empty_removes_key(self, mux_map):
        async def remove_this():
            pass

        mux_map._muxes["foo"] = [remove_this]

        mux_map.remove("foo", remove_this)

        assert "foo" not in mux_map._muxes

    def test_remove_when_list_not_left_empty_removes_coroutine_function(self, mux_map):
        async def remove_this():
            pass

        mux_map._muxes["foo"] = [remove_this, remove_this]

        mux_map.remove("foo", remove_this)

        assert mux_map._muxes["foo"] == [remove_this]

    def test_dispatch_to_existing_muxes(self, mux_map):
        mock_coro1 = mock.MagicMock()
        mock_coro_fn1 = mock.MagicMock(return_value=mock_coro1)
        mock_coro2 = mock.MagicMock()
        mock_coro_fn2 = mock.MagicMock(return_value=mock_coro2)
        mock_coro3 = mock.MagicMock()
        mock_coro_fn3 = mock.MagicMock(return_value=mock_coro3)

        mux_map._muxes["foo"] = [mock_coro_fn1, mock_coro_fn2]
        mux_map._muxes["bar"] = [mock_coro_fn3]

        args = ("a", "b", "c")

        with mock.patch("asyncio.gather") as gather:
            mux_map.dispatch("foo", *args)
            gather.assert_called_once_with(mock_coro1, mock_coro2)

        mock_coro_fn1.assert_called_once_with(*args)
        mock_coro_fn2.assert_called_once_with(*args)
        mock_coro_fn3.assert_not_called()

    def test_dispatch_to_non_existant_muxes(self, mux_map):
        # Should not throw.
        mux_map.dispatch("foo", "a", "b", "c")

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_nothing_is_invoked(self, mux_map):
        coro_fn = mock.AsyncMock()

        mux_map.add("foo", coro_fn)
        await mux_map.dispatch("bar")

    @pytest.mark.asyncio
    async def test_dispatch_is_awaitable_if_something_is_invoked(self, mux_map):
        coro_fn = mock.AsyncMock()

        mux_map.add("foo", coro_fn)
        await mux_map.dispatch("foo")


class TestCompletedFuture:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("args", [(), (12,)])
    async def test_is_awaitable(self, args):
        await aio.completed_future(*args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("args", [(), (12,)])
    async def test_is_completed(self, args):
        future = aio.completed_future(*args)
        assert future.done()

    @pytest.mark.asyncio
    async def test_default_result_is_none(self):
        assert aio.completed_future().result() is None

    @pytest.mark.asyncio
    async def test_non_default_result(self):
        assert aio.completed_future(...).result() is ...
