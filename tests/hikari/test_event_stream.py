# -*- coding: utf-8 -*-
# Copyright (c) 2020 Nekokatt
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
import logging
import unittest
import weakref

import mock
import pytest

from hikari import event_stream
from hikari import events
from hikari import iterators
from hikari.impl import bot
from tests.hikari import hikari_test_helpers


@pytest.mark.asyncio
async def test__generate_weak_listener_when_method_is_None():
    def test():
        return None

    call_weak_method = event_stream._generate_weak_listener(test)

    with pytest.raises(
        TypeError,
        match=r"dead weak referenced subscriber method cannot be executed, try actually closing your event streamers",
    ):
        await call_weak_method(None)


class TestStreamer:
    @pytest.fixture(scope="module")
    def stub_streamer(self):
        return hikari_test_helpers.mock_class_namespace(event_stream.Streamer)

    @pytest.mark.asyncio
    async def test___aenter___and___aexit__(self, stub_streamer):
        async with stub_streamer():
            stub_streamer.open.assert_awaited_once()
            stub_streamer.close.assert_not_called()

        stub_streamer.open.assert_awaited_once()
        stub_streamer.close.assert_awaited_once()

    def test___enter__(self, stub_streamer):
        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError, match=" is async-only, did you mean 'async with'?"):
            stub_streamer().__enter__()

    def test___exit__(self, stub_streamer):
        try:
            stub_streamer().__exit__(None, None, None)
        except AttributeError as exc:
            pytest.fail(exc)


@pytest.fixture()
def mock_app():
    return mock.Mock(bot.BotApp)


class TestEventStream:
    @pytest.mark.asyncio
    async def test__listener_when_filter_returns_false(self, mock_app):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None)
        stream.filter(lambda _: False)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 0

    @pytest.mark.asyncio
    async def test__listener_when_filter_passes_and_queue_full(self):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None, limit=2)
        stream._queue.put_nowait(object())
        stream._queue.put_nowait(object())
        stream.filter(lambda _: True)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 2
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is not mock_event

    @pytest.mark.asyncio
    async def test__listener_when_filter_passes_and_queue_not_full(self):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None, limit=None)
        stream._queue.put_nowait(object())
        stream._queue.put_nowait(object())
        stream.filter(lambda _: True)
        mock_event = object()

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 3
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is mock_event

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___when_stream_closed(self):
        streamer = hikari_test_helpers.mock_class_namespace(event_stream.EventStream, _active=False)(
            app=mock.Mock(), event_type=events.Event, timeout=float("inf")
        )

        # flake8 gets annoyed if we use "with" here so here's a hacky alternative
        with pytest.raises(TypeError):
            await streamer.__anext__()

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___times_out(self):
        streamer = hikari_test_helpers.mock_class_namespace(
            event_stream.EventStream,
            _active=True,
            _queue=asyncio.Queue(),
        )(app=mock.Mock(), event_type=events.Event, timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME)

        async with streamer:
            async for _ in streamer:
                pytest.fail("streamer shouldn't have yielded anything")

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext___waits_for_next_event(self):
        mock_event = object()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_stream.EventStream,
            _active=True,
            _queue=asyncio.Queue(),
        )(app=mock.Mock(), event_type=events.Event, timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME * 3)

        async def add_event():
            await asyncio.sleep(hikari_test_helpers.REASONABLE_SLEEP_TIME)
            streamer._queue.put_nowait(mock_event)

        asyncio.create_task(add_event())

        async with streamer:
            async for event in streamer:
                assert event is mock_event
                return

            pytest.fail("streamer should've yielded something")

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test___anext__(self):
        mock_event = object()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_stream.EventStream,
            _active=True,
            _queue=asyncio.Queue(),
        )(app=mock.Mock(), event_type=events.Event, timeout=hikari_test_helpers.REASONABLE_QUICK_RESPONSE_TIME)
        streamer._queue.put_nowait(mock_event)

        async with streamer:
            async for event in streamer:
                assert event is mock_event
                return

        pytest.fail("streamer should've yielded something")

    @pytest.mark.asyncio
    async def test___await__(self):
        mock_event_0 = object()
        mock_event_1 = object()
        mock_event_2 = object()
        streamer = hikari_test_helpers.mock_class_namespace(
            event_stream.EventStream,
            close=mock.AsyncMock(),
            open=mock.AsyncMock(),
            init_=False,
            __anext__=mock.AsyncMock(side_effect=[mock_event_0, mock_event_1, mock_event_2]),
        )()

        assert await streamer == [mock_event_0, mock_event_1, mock_event_2]
        streamer.open.assert_awaited_once()
        streamer.close.assert_awaited_once()

    def test___del___for_active_stream(self):
        mock_coroutine = object()
        close_method = mock.Mock(return_value=mock_coroutine)
        streamer = hikari_test_helpers.mock_class_namespace(event_stream.EventStream, close=close_method, init_=False)()
        streamer._event_type = events.Event
        streamer._active = True

        with mock.patch.object(asyncio, "ensure_future", side_effect=RuntimeError):
            with unittest.TestCase().assertLogs("hikari", level=logging.WARNING) as logging_watcher:
                del streamer

                assert logging_watcher.output == [
                    "WARNING:hikari:active 'Event' streamer fell out of scope before being closed"
                ]

            asyncio.ensure_future.assert_called_once_with(mock_coroutine)

        close_method.assert_called_once_with()

    def test___del___for_inactive_stream(self):
        close_method = mock.Mock()
        streamer = hikari_test_helpers.mock_class_namespace(event_stream.EventStream, close=close_method, init_=False)()
        streamer._event_type = events.Event
        streamer._active = False

        with mock.patch.object(asyncio, "ensure_future"):
            del streamer
            asyncio.ensure_future.assert_not_called()

        close_method.assert_not_called()

    @pytest.mark.asyncio
    async def test_close_for_inactive_stream(self, mock_app):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None, limit=None)
        await stream.close()
        mock_app.dispatcher.unsubscribe.assert_not_called()

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test_close_for_active_stream(self, mock_app):
        mock_registered_listener = object()
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock_app, event_type=events.Event, timeout=float("inf")
        )

        await stream.open()
        stream._registered_listener = mock_registered_listener
        await stream.close()
        mock_app.dispatcher.unsubscribe.assert_called_once_with(events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test_close_for_active_stream_handles_value_error(self, mock_app):
        mock_registered_listener = object()
        mock_app.dispatcher.unsubscribe.side_effect = ValueError
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock_app, event_type=events.Event, timeout=float("inf")
        )

        await stream.open()
        stream._registered_listener = mock_registered_listener
        await stream.close()
        mock_app.dispatcher.unsubscribe.assert_called_once_with(events.Event, mock_registered_listener)
        assert stream._active is False
        assert stream._registered_listener is None

    def test_filter_for_inactive_stream(self):
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock.Mock(), event_type=events.Event, timeout=1
        )
        stream._filters = iterators.All(())
        first_pass = mock.Mock(attr=True)
        second_pass = mock.Mock(attr=True)
        first_fails = mock.Mock(attr=True)
        second_fail = mock.Mock(attr=False)

        def predicate(obj):
            return obj in (first_pass, second_pass)

        stream.filter(predicate, attr=True)

        assert stream._filters(first_pass) is True
        assert stream._filters(first_fails) is False
        assert stream._filters(second_pass) is True
        assert stream._filters(second_fail) is False

    @pytest.mark.asyncio
    async def test_filter_for_active_stream(self):
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock.Mock(), event_type=events.Event, timeout=float("inf")
        )
        stream._active = True
        mock_wrapping_iterator = object()
        predicate = object()

        with mock.patch.object(iterators.LazyIterator, "filter", return_value=mock_wrapping_iterator):
            assert stream.filter(predicate, name="OK") is mock_wrapping_iterator

            iterators.LazyIterator.filter.assert_called_once_with(predicate, name="OK")

        # Ensure we don't get a warning or error on del
        stream._active = False

    @pytest.mark.asyncio
    async def test_open_for_inactive_stream(self, mock_app):
        mock_listener = object()
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock_app,
            event_type=events.Event,
            timeout=float("inf"),
        )

        stream._active = True
        stream._registered_listener = mock_listener

        with mock.patch.object(event_stream, "_generate_weak_listener"):
            with mock.patch.object(weakref, "WeakMethod"):
                await stream.open()

                weakref.WeakMethod.assert_not_called()
            event_stream._generate_weak_listener.assert_not_called()

        mock_app.dispatcher.subscribe.assert_not_called()
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False

    @pytest.mark.asyncio
    @hikari_test_helpers.timeout()
    async def test_open_for_active_stream(self, mock_app):
        stream = hikari_test_helpers.mock_class_namespace(event_stream.EventStream)(
            app=mock_app, event_type=events.Event, timeout=float("inf")
        )
        stream._active = False
        mock_listener = object()
        mock_listener_ref = object()

        with mock.patch.object(event_stream, "_generate_weak_listener", return_value=mock_listener):
            with mock.patch.object(weakref, "WeakMethod", return_value=mock_listener_ref):
                await stream.open()

                weakref.WeakMethod.assert_called_once_with(stream._listener)
            event_stream._generate_weak_listener.assert_called_once_with(mock_listener_ref)

        mock_app.dispatcher.subscribe.assert_called_once_with(events.Event, mock_listener)
        assert stream._active is True
        assert stream._registered_listener is mock_listener

        # Ensure we don't get a warning or error on del
        stream._active = False
