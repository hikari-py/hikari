# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
# Copyright (c) 2021-present davfsa
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import asyncio
import contextlib
import math
import sys
import time

import mock
import pytest

from hikari.impl import rate_limits
from tests.hikari import hikari_test_helpers


class MockFuture(mock.Mock):
    def __await__(self):
        if False:
            yield  # Turns this into a generator.
        return None


class TestBaseRateLimiter:
    def test_context_management(self):
        class MockedBaseRateLimiter(rate_limits.BaseRateLimiter):
            close = mock.Mock()
            acquire = NotImplemented

        with MockedBaseRateLimiter() as m:
            pass

        m.close.assert_called_once()


class TestBurstRateLimiter:
    @pytest.fixture()
    def mock_burst_limiter(self):
        class Impl(rate_limits.BurstRateLimiter):
            async def acquire(self, *args, **kwargs) -> None:
                raise NotImplementedError

        return Impl(__name__)

    @pytest.mark.parametrize(("queue", "is_empty"), [(["foo", "bar", "baz"], False), ([], True)])
    def test_is_empty(self, queue, is_empty, mock_burst_limiter):
        mock_burst_limiter.queue = queue
        assert mock_burst_limiter.is_empty is is_empty

    @pytest.mark.asyncio()
    async def test_close_removes_all_futures_from_queue(self, mock_burst_limiter):
        event_loop = asyncio.get_running_loop()
        mock_burst_limiter.throttle_task = None
        futures = [event_loop.create_future() for _ in range(10)]
        mock_burst_limiter.queue = list(futures)
        mock_burst_limiter.close()
        assert len(mock_burst_limiter.queue) == 0

    @pytest.mark.asyncio()
    async def test_close_cancels_all_futures_pending_when_futures_pending(self, mock_burst_limiter):
        event_loop = asyncio.get_running_loop()
        mock_burst_limiter.throttle_task = None
        futures = [event_loop.create_future() for _ in range(10)]
        mock_burst_limiter.queue = list(futures)
        mock_burst_limiter.close()
        for i, future in enumerate(futures):
            assert future.cancelled(), f"future {i} was not cancelled"

    @pytest.mark.asyncio()
    async def test_close_is_silent_when_no_futures_pending(self, mock_burst_limiter):
        mock_burst_limiter.throttle_task = None
        mock_burst_limiter.queue = []
        mock_burst_limiter.close()
        assert True, "passed successfully"

    @pytest.mark.asyncio()
    async def test_close_cancels_throttle_task_if_running(self, mock_burst_limiter):
        event_loop = asyncio.get_running_loop()
        task = event_loop.create_future()
        mock_burst_limiter.throttle_task = task
        mock_burst_limiter.close()
        assert mock_burst_limiter.throttle_task is None, "task was not overwritten with None"
        assert task.cancelled(), "throttle_task is not cancelled"

    @pytest.mark.asyncio()
    async def test_close_when_closed(self, mock_burst_limiter):
        # Double-running shouldn't do anything adverse.
        mock_burst_limiter.close()
        mock_burst_limiter.close()


class TestManualRateLimiter:
    @pytest.mark.asyncio()
    async def test_acquire_returns_completed_future_if_throttle_task_is_None(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.ManualRateLimiter() as limiter:
            limiter.throttle_task = None
            future = MockFuture()
            event_loop.create_future = mock.Mock(return_value=future)

            await limiter.acquire()
            future.set_result.assert_called_once_with(None)

    @pytest.mark.asyncio()
    async def test_acquire_returns_incomplete_future_if_throttle_task_is_not_None(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.ManualRateLimiter() as limiter:
            limiter.throttle_task = event_loop.create_future()
            future = MockFuture()
            event_loop.create_future = mock.Mock(return_value=future)

            await limiter.acquire()
            future.set_result.assert_not_called()

    @pytest.mark.asyncio()
    async def test_acquire_places_future_on_queue_if_throttle_task_is_not_None(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.ManualRateLimiter() as limiter:
            limiter.throttle_task = event_loop.create_future()
            future = MockFuture()
            event_loop.create_future = mock.Mock(return_value=future)

            assert len(limiter.queue) == 0

            await limiter.acquire()

            assert len(limiter.queue) == 1
            assert future in limiter.queue
            future.set_result.assert_not_called()

    @pytest.mark.asyncio()
    async def test_throttle_cancels_existing_task(self):
        with rate_limits.ManualRateLimiter() as limiter:
            limiter.throttle_task = asyncio.get_running_loop().create_future()
            old_task = limiter.throttle_task
            limiter.throttle(0)
            assert old_task.cancelled()
            assert old_task is not limiter.throttle_task

    @pytest.mark.asyncio()
    async def test_throttle_schedules_throttle(self):
        with hikari_test_helpers.mock_class_namespace(rate_limits.ManualRateLimiter, slots_=False)() as limiter:
            limiter.unlock_later = mock.AsyncMock()
            limiter.throttle(0)
            await limiter.throttle_task
            limiter.unlock_later.assert_called_once_with(0)

    @pytest.mark.asyncio()
    async def test_throttle_chews_queue_completing_futures(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.ManualRateLimiter() as limiter:
            futures = [event_loop.create_future() for _ in range(10)]
            limiter.queue = list(futures)
            await limiter.unlock_later(0.01)
            for i, future in enumerate(futures):
                assert future.done(), f"future {i} was not done"

    @pytest.mark.asyncio()
    async def test_throttle_sleeps_before_popping_queue(self):
        event_loop = asyncio.get_running_loop()
        # GIVEN
        slept_at = float("nan")
        popped_at = []

        async def mock_sleep(_):
            nonlocal slept_at
            slept_at = time.perf_counter()

        class MockList(list):
            def pop(self, _=-1):
                popped_at.append(time.perf_counter())
                return event_loop.create_future()

        with hikari_test_helpers.mock_class_namespace(rate_limits.ManualRateLimiter, slots_=False)() as limiter:
            with mock.patch("asyncio.sleep", wraps=mock_sleep):
                limiter.queue = MockList()

                # WHEN
                await limiter.unlock_later(5)

        # THEN
        for i, pop_time in enumerate(popped_at):
            assert slept_at < pop_time, f"future {i} popped before initial sleep"

    @pytest.mark.asyncio()
    async def test_throttle_clears_throttle_task(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.ManualRateLimiter() as limiter:
            limiter.throttle_task = event_loop.create_future()
            await limiter.unlock_later(0)
        assert limiter.throttle_task is None


class TestWindowedBurstRateLimiter:
    @pytest.fixture()
    def ratelimiter(self):
        inst = hikari_test_helpers.mock_class_namespace(rate_limits.WindowedBurstRateLimiter, slots_=False)(
            __name__, 3, 3
        )
        yield inst
        with contextlib.suppress(Exception):
            inst.close()

    @pytest.mark.asyncio()
    async def test_drip_if_not_throttled_and_not_ratelimited(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = None
        ratelimiter.is_rate_limited = mock.Mock(return_value=False)
        event_loop.create_future = mock.Mock()

        await ratelimiter.acquire()

        ratelimiter.drip.assert_called_once_with()
        event_loop.create_future.assert_not_called()

    @pytest.mark.asyncio()
    async def test_no_drip_if_throttle_task_is_not_None(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = asyncio.get_running_loop().create_future()
        ratelimiter.is_rate_limited = mock.Mock(return_value=False)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        await ratelimiter.acquire()

        ratelimiter.drip.assert_not_called()

    @pytest.mark.asyncio()
    async def test_no_drip_if_rate_limited(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = False
        ratelimiter.is_rate_limited = mock.Mock(return_value=True)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        await ratelimiter.acquire()

        ratelimiter.drip.assert_not_called()

    @pytest.mark.asyncio()
    async def test_task_scheduled_if_rate_limited_and_throttle_task_is_None(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = None
        ratelimiter.throttle = mock.AsyncMock()
        ratelimiter.is_rate_limited = mock.Mock(return_value=True)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        await ratelimiter.acquire()
        assert ratelimiter.throttle_task is not None

        ratelimiter.throttle.assert_called()

    @pytest.mark.asyncio()
    async def test_task_not_scheduled_if_rate_limited_and_throttle_task_not_None(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = event_loop.create_future()
        old_task = ratelimiter.throttle_task
        ratelimiter.is_rate_limited = mock.Mock(return_value=True)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        await ratelimiter.acquire()
        assert old_task is ratelimiter.throttle_task, "task was rescheduled, that shouldn't happen :("

    @pytest.mark.asyncio()
    async def test_future_is_added_to_queue_if_throttle_task_is_not_None(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = asyncio.get_running_loop().create_future()
        ratelimiter.is_rate_limited = mock.Mock(return_value=False)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        await ratelimiter.acquire()

        # use slice to prevent aborting test with index error rather than assertion error if this fails.
        assert ratelimiter.queue[-1:] == [future]

    @pytest.mark.asyncio()
    async def test_future_is_added_to_queue_if_rate_limited(self, ratelimiter):
        event_loop = asyncio.get_running_loop()

        ratelimiter.drip = mock.Mock()
        ratelimiter.throttle_task = None
        ratelimiter.is_rate_limited = mock.Mock(return_value=True)
        future = MockFuture()
        event_loop.create_future = mock.Mock(return_value=future)

        try:
            await ratelimiter.acquire()
            # use slice to prevent aborting test with index error rather than assertion error if this fails.
            assert ratelimiter.queue[-1:] == [future]
        finally:
            ratelimiter.throttle_task.cancel()

    @pytest.mark.asyncio()
    async def test_throttle_consumes_queue(self):
        event_loop = asyncio.get_running_loop()

        with mock.patch.object(asyncio, "sleep"):
            with rate_limits.WindowedBurstRateLimiter(__name__, 0.001, 1) as rl:
                rl.queue = [event_loop.create_future() for _ in range(15)]
                old_queue = list(rl.queue)
                await rl.throttle()

        assert len(rl.queue) == 0
        for i, future in enumerate(old_queue):
            assert future.done(), f"future {i} was incomplete!"

    @pytest.mark.asyncio()
    async def test_throttle_when_limited_sleeps_then_bursts_repeatedly(self):
        event_loop = asyncio.get_running_loop()

        window = 5
        loop_count = 0
        futures = [event_loop.create_future() for _ in range(20)]
        reset_time_iter = iter(range(int(len(futures) / window)))

        def mock_get_time_until_reset(_self, _):
            nonlocal loop_count

            for i, future in enumerate(futures):
                if i >= (window * loop_count):
                    assert not future.done(), f"future {i} was complete, expected it to be incomplete!"
                else:
                    assert future.done(), f"future {i} was incomplete, expected it to be completed!"

            loop_count += 1

            rl.remaining = window

            return next(reset_time_iter)

        stack = contextlib.ExitStack()
        rl = stack.enter_context(rate_limits.WindowedBurstRateLimiter(__name__, 0, window))
        stack.enter_context(
            mock.patch.object(
                rate_limits.WindowedBurstRateLimiter, "get_time_until_reset", new=mock_get_time_until_reset
            )
        )
        stack.enter_context(mock.patch.object(asyncio, "sleep"))

        with stack:
            rl.queue = list(futures)
            rl.reset_at = time.perf_counter()
            await rl.throttle()
            # die if we take too long...
            await asyncio.wait(futures, timeout=3)

        assert loop_count == 4
        assert len(rl.queue) == 0
        for i, future in enumerate(futures):
            assert future.done(), f"future {i} was incomplete!"

    @pytest.mark.asyncio()
    async def test_throttle_resets_throttle_task(self):
        event_loop = asyncio.get_running_loop()

        with rate_limits.WindowedBurstRateLimiter(__name__, 0.001, 1) as rl:
            rl.queue = [event_loop.create_future() for _ in range(15)]
            rl.throttle_task = None
            await rl.throttle()
        assert rl.throttle_task is None

    def test_get_time_until_reset_if_not_rate_limited(self):
        with hikari_test_helpers.mock_class_namespace(rate_limits.WindowedBurstRateLimiter, slots_=False)(
            __name__, 0.01, 1
        ) as rl:
            rl.is_rate_limited = mock.Mock(return_value=False)
            assert rl.get_time_until_reset(420) == 0.0

    def test_get_time_until_reset_if_rate_limited(self):
        with hikari_test_helpers.mock_class_namespace(rate_limits.WindowedBurstRateLimiter, slots_=False)(
            __name__, 0.01, 1
        ) as rl:
            rl.is_rate_limited = mock.Mock(return_value=True)
            rl.reset_at = 420.4
            assert rl.get_time_until_reset(69.8) == 420.4 - 69.8

    def test_is_rate_limited_when_rate_limit_expired_resets_self(self):
        with rate_limits.WindowedBurstRateLimiter(__name__, 403, 27) as rl:
            now = 180
            rl.reset_at = 80
            rl.remaining = 4

            assert not rl.is_rate_limited(now)

            assert rl.reset_at == now + 403
            assert rl.remaining == 27

    @pytest.mark.parametrize("remaining", [-1, 0, 1])
    def test_is_rate_limited_when_rate_limit_not_expired_only_returns_False(self, remaining):
        with rate_limits.WindowedBurstRateLimiter(__name__, 403, 27) as rl:
            now = 420
            rl.reset_at = now + 69
            rl.remaining = remaining
            assert rl.is_rate_limited(now) is (remaining <= 0)


class TestExponentialBackOff:
    def test___init___raises_on_too_large_int_base(self):
        base = int(sys.float_info.max) + int(sys.float_info.max * 1 / 100)
        with pytest.raises(ValueError, match="int too large to be represented as a float"):
            rate_limits.ExponentialBackOff(base=base)

    def test___init___raises_on_too_large_int_maximum(self):
        maximum = int(sys.float_info.max) + int(sys.float_info.max * 1 / 200)
        with pytest.raises(ValueError, match="int too large to be represented as a float"):
            rate_limits.ExponentialBackOff(maximum=maximum)

    def test___init___raises_on_too_large_int_jitter_multiplier(self):
        jitter_multiplier = int(sys.float_info.max) + int(sys.float_info.max * 1 / 300)
        with pytest.raises(ValueError, match="int too large to be represented as a float"):
            rate_limits.ExponentialBackOff(jitter_multiplier=jitter_multiplier)

    def test___init___raises_on_not_finite_base(self):
        with pytest.raises(ValueError, match="base must be a finite number"):
            rate_limits.ExponentialBackOff(base=float("inf"))

    def test___init___raises_on_not_finite_maximum(self):
        with pytest.raises(ValueError, match="maximum must be a finite number"):
            rate_limits.ExponentialBackOff(maximum=float("nan"))

    def test___init___raises_on_not_finite_jitter_multiplier(self):
        with pytest.raises(ValueError, match="jitter_multiplier must be a finite number"):
            rate_limits.ExponentialBackOff(jitter_multiplier=float("inf"))

    def test_reset(self):
        eb = rate_limits.ExponentialBackOff()
        eb.increment = 10
        eb.reset()
        assert eb.increment == 0

    @pytest.mark.parametrize(("iteration", "backoff"), enumerate((1, 2, 4, 8, 16, 32)))
    def test_increment_linear(self, iteration, backoff):
        eb = rate_limits.ExponentialBackOff(2, 64, 0)

        for _ in range(iteration):
            next(eb)

        assert next(eb) == backoff

    def test_increment_raises_on_numerical_limitation(self):
        power = math.log(sys.float_info.max, 5) + 0.5
        eb = rate_limits.ExponentialBackOff(
            base=5, maximum=sys.float_info.max, jitter_multiplier=0.0, initial_increment=power
        )

        assert next(eb) == sys.float_info.max

    def test_increment_maximum(self):
        max_bound = 64
        eb = rate_limits.ExponentialBackOff(2, max_bound, 0)
        iterations = math.ceil(math.log2(max_bound))
        for _ in range(iterations):
            next(eb)

        assert next(eb) == max_bound

    def test_increment_does_not_increment_when_on_maximum(self):
        eb = rate_limits.ExponentialBackOff(2, 32, initial_increment=5, jitter_multiplier=0)

        assert eb.increment == 5

        assert next(eb) == 32

        assert eb.increment == 5

    @pytest.mark.parametrize(("iteration", "backoff"), enumerate((1, 2, 4, 8, 16, 32)))
    def test_increment_jitter(self, iteration, backoff):
        abs_tol = 1
        eb = rate_limits.ExponentialBackOff(2, 64, abs_tol)

        for _ in range(iteration):
            next(eb)

        assert math.isclose(next(eb), backoff, abs_tol=abs_tol)

    def test_iter_returns_self(self):
        eb = rate_limits.ExponentialBackOff(2, 64, 123)
        assert iter(eb) is eb
