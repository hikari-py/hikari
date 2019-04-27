#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import asynctest
import async_timeout

from nose.tools import assert_equal, assert_raises

from hikari.utils import backoff


class RetryTest(asynctest.TestCase):
    async def test_retry_success_case(self):
        count = 0
        try:
            # Give up after 10 seconds as it has clearly failed.
            with async_timeout.timeout(10):
                @backoff.retry(transform=lambda b, i: b ** i / 100, backoff_base=2)
                def fail_five_times(arg):
                    nonlocal count
                    if count < 5:
                        count += 1
                        raise RuntimeError('test')
                    else:
                        return 'Finished! ' + arg

                result = await fail_five_times(":)")

                assert_equal("Finished! :)", result, 'Did not output expected result')

                assert_equal(5, count, "Did not retry 5 times...")
        except asyncio.TimeoutError as ex:
            raise AssertionError(f"Timeout was hit, retry ran {count} times, did it get stuck?") from ex

    async def test_retry_when_no_failure_passes_through_normally(self):
        with async_timeout.timeout(0.1):
            @backoff.retry()
            def pass_always():
                return 12

            assert_equal(12, await pass_always())

    async def test_retry_throws_implicit_fatal_exception(self):
        with assert_raises(FloatingPointError), async_timeout.timeout(10):
            @backoff.retry(fatal_on=(), retry_on=(IndexError,))
            def fail_immediately():
                raise FloatingPointError

            await fail_immediately()

    async def test_retry_throws_explicit_fatal_exception(self):
        with assert_raises(FloatingPointError), async_timeout.timeout(10):
            @backoff.retry(fatal_on=(FloatingPointError,), retry_on=(IndexError,))
            def fail_immediately():
                raise FloatingPointError

            await fail_immediately()

    async def test_retry_timeout(self):
        with async_timeout.timeout(5):
            with assert_raises(asyncio.TimeoutError):
                @backoff.retry(retry_on=(FloatingPointError,), timeout=0.25)
                def fail_immediately():
                    raise FloatingPointError

                await fail_immediately()

    async def test_retry_fatal_on_overrides_retry_on_args(self):
        with async_timeout.timeout(5):
            with assert_raises(FloatingPointError):
                @backoff.retry(retry_on=(FloatingPointError,), fatal_on=(FloatingPointError,))
                def fail_immediately():
                    raise FloatingPointError
                await fail_immediately()
