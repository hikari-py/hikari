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
import mock
import pytest

from hikari import scheduled_events
from hikari import snowflakes
from hikari import urls
from hikari.internal import routes
from tests.hikari import hikari_test_helpers


class TestScheduledEvent:
    @pytest.fixture
    def model(self) -> scheduled_events.ScheduledEvent:
        return hikari_test_helpers.mock_class_namespace(scheduled_events.ScheduledEvent, init_=False, slots_=False)()

    def test_image_url_property(self, model: scheduled_events.ScheduledEvent):
        model.make_image_url = mock.Mock()

        assert model.image_url == model.make_image_url.return_value

        model.make_image_url.assert_called_once_with()

    def test_image_url(self, model: scheduled_events.ScheduledEvent):
        model.id = snowflakes.Snowflake(543123)
        model.image_hash = "ododododo"
        with mock.patch.object(routes, "SCHEDULED_EVENT_COVER") as route:
            assert model.make_image_url(ext="jpeg", size=1) is route.compile_to_file.return_value

        route.compile_to_file.assert_called_once_with(
            urls.CDN_URL, scheduled_event_id=543123, hash="ododododo", size=1, file_format="jpeg"
        )

    def test_make_image_url_when_image_hash_is_none(self, model: scheduled_events.ScheduledEvent):
        model.image_hash = None

        with mock.patch.object(routes, "SCHEDULED_EVENT_COVER") as route:
            assert model.make_image_url(ext="jpeg", size=1) is None

        route.compile_to_file.assert_not_called()
