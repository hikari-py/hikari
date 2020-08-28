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

import mock
import pytest

from hikari import events
from hikari.impl import bot
from hikari.utilities import event_stream
from tests.hikari import hikari_test_helpers


class TestStreamer:
    @pytest.mark.asyncio
    async def test___aenter___and___aexit__(self):
        mock_streamer = hikari_test_helpers.mock_class_namespace(event_stream.Streamer)
        async with mock_streamer():
            mock_streamer.open.assert_called_once()
            mock_streamer.close.assert_not_called()

        mock_streamer.open.assert_called_once()
        mock_streamer.close.assert_called_once()

    def test___enter___and___exit__(self):
        mock_streamer = hikari_test_helpers.mock_class_namespace(event_stream.Streamer)

        with pytest.raises(TypeError):
            with mock_streamer():
                ...


@pytest.fixture()
def mock_app():
    return mock.Mock(bot.BotApp)


class TestEventStream:
    @pytest.mark.asyncio
    async def test__listener_when_filter_returns_false(self, mock_app):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None)
        stream.filter(lambda _: False)
        mock_event = mock.Mock(events.Event)

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 0

    @pytest.mark.asyncio
    async def test__listener_when_filter_passes_and_queue_full(self):
        stream = event_stream.EventStream(mock_app, events.Event, timeout=None, limit=2)
        stream._queue.put_nowait(object())
        stream._queue.put_nowait(object())
        stream.filter(lambda _: True)
        mock_event = mock.Mock(events.Event)

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
        mock_event = mock.Mock(events.Event)

        assert await stream._listener(mock_event) is None
        assert stream._queue.qsize() == 3
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is not mock_event
        assert stream._queue.get_nowait() is mock_event

    @pytest.mark.asyncio
    def test___anext__(self):
        ...

    @pytest.mark.asyncio
    def test___await__(self):
        ...

    def test___del___for_active_stream(self):
        mock_coroutine = object()
        close_method = mock.Mock(return_value=mock_coroutine)
        streamer = hikari_test_helpers.mock_class_namespace(event_stream.EventStream, close=close_method, init=False)()
        streamer._event_type = events.Event
        streamer._active = True

        with mock.patch.object(asyncio, "ensure_future", return_value=mock_coroutine):
            with unittest.TestCase().assertLogs("hikari", level=logging.WARNING) as logging_watcher:
                del streamer

                assert logging_watcher.output == [
                    "WARNING:hikari:active 'Event' streamer fell out of scope before being closed"
                ]

            asyncio.ensure_future.assert_called_once_with(mock_coroutine)

        close_method.assert_called_once()

    def test___del___for_inactive_stream(self):
        close_method = mock.Mock()
        streamer = hikari_test_helpers.mock_class_namespace(event_stream.EventStream, close=close_method, init=False)()
        streamer._event_type = events.Event
        streamer._active = False

        with mock.patch.object(asyncio, "ensure_future"):
            del streamer
            asyncio.ensure_future.assert_not_called()

        close_method.assert_not_called()

    def test_close(self):
        ...

    def test_filter_for_inactive_stream(self):
        ...

    def test_filter_for_active_stream(self):
        ...

    def test_open_for_inactive_stream(self):
        ...

    def test_open_for_active_stream(self):
        ...
