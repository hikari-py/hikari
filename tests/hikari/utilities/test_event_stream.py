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
import typing

import mock
import pytest

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


class TestEventStream:
    def test__listener(self):
        ...

    def test___anext__(self):
        ...

    def test___await__(self):
        ...

    def test___del___for_active_stream(self):
        ...

    def test___del___for_inactive_stream(self):
        ...

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
