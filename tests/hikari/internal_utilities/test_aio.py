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

import async_timeout
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
        assert coro_fn in mux_map._listeners["foo"]

    def test_add_coroutine_function_when_list_exists(self, mux_map):
        async def coro_fn1():
            pass

        async def coro_fn2():
            pass

        mux_map.add("foo", coro_fn1)
        mux_map.add("foo", coro_fn2)
        assert coro_fn1 in mux_map._listeners["foo"]
        assert coro_fn2 in mux_map._listeners["foo"]

    def test_remove_non_existing_mux_list(self, mux_map):
        async def remove_this():
            pass

        # should not raise
        mux_map.remove("foo", remove_this)

    def test_remove_non_existing_mux(self, mux_map):
        mux_map._listeners["foo"] = []

        async def remove_this():
            pass

        # should not raise
        mux_map.remove("foo", remove_this)

    def test_remove_when_list_left_empty_removes_key(self, mux_map):
        async def remove_this():
            pass

        mux_map._listeners["foo"] = [remove_this]

        mux_map.remove("foo", remove_this)

        assert "foo" not in mux_map._listeners

    def test_remove_when_list_not_left_empty_removes_coroutine_function(self, mux_map):
        async def remove_this():
            pass

        mux_map._listeners["foo"] = [remove_this, remove_this]

        mux_map.remove("foo", remove_this)

        assert mux_map._listeners["foo"] == [remove_this]

    def test_dispatch_to_existing_muxes(self, mux_map):
        mock_coro1 = mock.MagicMock()
        mock_coro_fn1 = mock.MagicMock(return_value=mock_coro1)
        mock_coro2 = mock.MagicMock()
        mock_coro_fn2 = mock.MagicMock(return_value=mock_coro2)
        mock_coro3 = mock.MagicMock()
        mock_coro_fn3 = mock.MagicMock(return_value=mock_coro3)

        mux_map._listeners["foo"] = [mock_coro_fn1, mock_coro_fn2]
        mux_map._listeners["bar"] = [mock_coro_fn3]

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

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_return", (True, False))
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"),
        [
            ((), None,),
            ((12,), 12),
            ((12, 22, 33), (12, 22, 33))
        ]
    )
    @_helpers.timeout_after(1)
    async def test_dispatch_awakens_matching_futures(
        self, mux_map, event_loop, predicate_return, in_event_args, expected_result
    ):
        future1 = event_loop.create_future()
        future2 = event_loop.create_future()
        future3 = event_loop.create_future()
        future4 = event_loop.create_future()

        predicate1 = mock.MagicMock(return_value=predicate_return)
        predicate2 = mock.MagicMock(return_value=predicate_return)
        predicate3 = mock.MagicMock(return_value=True)
        predicate4 = mock.MagicMock(return_value=False)

        mux_map._waiters["foobar"] = {}
        mux_map._waiters["barbaz"] = {future3: predicate3}
        mux_map._waiters["foobar"][future1] = predicate1
        mux_map._waiters["foobar"][future2] = predicate2
        # Shouldn't be invoked, as the predicate is always false-returning.
        mux_map._waiters["foobar"][future4] = predicate4

        await mux_map.dispatch("foobar", *in_event_args)

        assert future1.done() is predicate_return
        predicate1.assert_called_once_with(*in_event_args)
        assert future2.done() is predicate_return
        predicate2.assert_called_once_with(*in_event_args)
        assert future3.done() is False
        predicate3.assert_not_called()
        assert future4.done() is False
        predicate4.assert_called_once_with(*in_event_args)

        if predicate_return:
            assert await future1 == expected_result
            assert await future2 == expected_result

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_return", (True, False))
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"),
        [
            ((), None,),
            ((12,), 12),
            ((12, 22, 33), (12, 22, 33))
        ]
    )
    @_helpers.timeout_after(1)
    async def test_dispatch_removes_awoken_future(
        self, mux_map, event_loop, predicate_return, in_event_args, expected_result
    ):
        future = event_loop.create_future()

        predicate = mock.MagicMock()

        mux_map._waiters["foobar"] = {}
        mux_map._waiters["foobar"][future] = predicate
        # Add a second future that never gets hit so the weakref map is not dropped from being
        # empty.
        mux_map._waiters["foobar"][event_loop.create_future()] = lambda *_: False

        await mux_map.dispatch("foobar", *in_event_args)
        predicate.assert_called_once_with(*in_event_args)
        predicate.reset_mock()

        await mux_map.dispatch("foobar", *in_event_args)
        predicate.assert_not_called()
        assert future not in mux_map._waiters["foobar"]

    @pytest.mark.asyncio
    @_helpers.timeout_after(1)
    async def test_dispatch_returns_exception_to_caller(self, mux_map, event_loop):
        predicate1 = mock.MagicMock(side_effect=RuntimeError())
        predicate2 = mock.MagicMock(return_value=False)

        future1 = event_loop.create_future()
        future2 = event_loop.create_future()

        mux_map._waiters["foobar"] = {}
        mux_map._waiters["foobar"][future1] = predicate1
        mux_map._waiters["foobar"][future2] = predicate2

        await mux_map.dispatch("foobar", object(), object(), object())

        try:
            await future1
            assert False, "No RuntimeError propagated :("
        except RuntimeError:
            pass

        # Isn't done, should raise InvalidStateError.
        try:
            future2.exception()
            assert False, "this future should still be running but isn't!"
        except asyncio.InvalidStateError:
            pass

    @pytest.mark.asyncio
    async def test_waiter_map_deleted_if_already_empty(self, mux_map):
        mux_map._waiters["foobar"] = {}
        await mux_map.dispatch("foobar")
        assert "foobar" not in mux_map._waiters

    @pytest.mark.asyncio
    async def test_waiter_map_deleted_if_made_empty_during_this_dispatch(self, mux_map):
        mux_map._waiters["foobar"] = {mock.MagicMock(): mock.MagicMock(return_value=True)}
        await mux_map.dispatch("foobar")
        assert "foobar" not in mux_map._waiters

    @pytest.mark.asyncio
    async def test_waiter_map_not_deleted_if_not_empty(self, mux_map):
        mux_map._waiters["foobar"] = {mock.MagicMock(): mock.MagicMock(return_value=False)}
        await mux_map.dispatch("foobar")
        assert "foobar" in mux_map._waiters

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"),
        [
            ((), None,),
            ((12,), 12),
            ((12, 22, 33), (12, 22, 33))
        ]
    )
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked(self, mux_map, in_event_args, expected_result):
        predicate = mock.MagicMock(return_value=True)
        future = mux_map.wait_for("foobar", timeout=5, predicate=predicate)

        await mux_map.dispatch("foobar", *in_event_args)

        await asyncio.sleep(0.5)

        assert future.done()
        actual_result = await future
        assert actual_result == expected_result
        predicate.assert_called_once_with(*in_event_args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("in_event_args", "expected_result"),
        [
            ((), None,),
            ((12,), 12),
            ((12, 22, 33), (12, 22, 33))
        ]
    )
    @_helpers.timeout_after(2)
    async def test_wait_for_returns_matching_event_args_when_invoked_but_no_predicate_match(
        self, mux_map, in_event_args, expected_result
    ):
        predicate = mock.MagicMock(return_value=False)
        future = mux_map.wait_for("foobar", timeout=5, predicate=predicate)
        await mux_map.dispatch("foobar", *in_event_args)

        await asyncio.sleep(0.5)

        assert not future.done()
        predicate.assert_called_once_with(*in_event_args)

    @pytest.mark.asyncio
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_wait_for_hits_timeout_and_raises(self, mux_map):
        predicate = mock.MagicMock(return_value=False)
        await mux_map.wait_for("foobar", timeout=1, predicate=predicate)
        assert False, "event was marked as succeeded when it shouldn't have been"


    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @_helpers.assert_raises(type_=RuntimeError)
    async def test_wait_for_raises_predicate_errors(self, mux_map):
        predicate = mock.MagicMock(side_effect=RuntimeError)
        future = mux_map.wait_for("foobar", timeout=1, predicate=predicate)
        await mux_map.dispatch("foobar", object())
        await future

    @pytest.mark.asyncio
    @pytest.mark.parametrize("predicate_side_effect", (True, False, RuntimeError()))
    @_helpers.timeout_after(5)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_other_events_in_same_waiter_event_name_do_not_awaken_us(self, mux_map, predicate_side_effect, event_loop):
        mux_map._waiters["foobar"] = {event_loop.create_future(): mock.MagicMock(side_effect=predicate_side_effect)}

        future = mux_map.wait_for("foobar", timeout=1, predicate=mock.MagicMock(return_value=False))

        await asyncio.gather(future, *(mux_map.dispatch("foobar") for _ in range(5)))


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


class TestMaybeTimeout:
    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @pytest.mark.parametrize("wait_for", (0, -1, -1.5, None))
    async def test_never_times_out_if_cannot_wait(self, wait_for):
        try:
            async with async_timeout.timeout(1):
                try:
                    async with aio.maybe_timeout(wait_for):
                        await asyncio.sleep(100)
                    assert False, "asyncio.sleep completed, but it should have hit the test timeout"
                except asyncio.TimeoutError:
                    assert False, "timed out unexpectedly"
            # noinspection PyUnreachableCode
            assert False, "did not time out"
        except asyncio.TimeoutError:
            pass

    @pytest.mark.asyncio
    @_helpers.timeout_after(2)
    @_helpers.assert_raises(type_=asyncio.TimeoutError)
    async def test_times_out(self):
        async with aio.maybe_timeout(1):
            await asyncio.sleep(100)
